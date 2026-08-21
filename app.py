from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient

from speech_to_text import transcribe_audio
from user_parser import parse_user

import os
import tempfile

load_dotenv()

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type"]
)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Backend is running"
    }), 200


# =========================================================
# MONGODB CONNECTION
# =========================================================

mongo_uri = os.getenv("MONGO_URI")

client = MongoClient(mongo_uri)
db = client["voice_user_db"]
users_collection = db["users"]


# =========================================================
# GET NEXT USER ID
# =========================================================

def get_next_user_id():

    last_user = users_collection.find_one(
        {"user_id": {"$exists": True}},
        sort=[("user_id", -1)]
    )

    if last_user:
        return last_user["user_id"] + 1

    return 1


# =========================================================
# CREATE USER
# =========================================================

@app.route("/users", methods=["POST"])
def create_user():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return jsonify({
            "error": "Name and email are required"
        }), 400

    user_id = get_next_user_id()

    user = {
        "user_id": user_id,
        "name": name,
        "email": email
    }

    users_collection.insert_one(user)

    created_user = {
        "id": user_id,
        "name": name,
        "email": email
    }

    return jsonify(created_user), 201


# =========================================================
# GET USERS
# =========================================================

@app.route("/users", methods=["GET"])
def get_users():

    users = []

    for user in users_collection.find():

        # Ignore incomplete/old documents
        if "user_id" not in user:
            continue

        users.append({
            "id": user.get("user_id"),
            "name": user.get("name"),
            "email": user.get("email")
        })

    return jsonify(users), 200


# =========================================================
# UPDATE USER
# =========================================================

@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):

    data = request.get_json()

    update_data = {}

    if data.get("name"):
        update_data["name"] = data["name"]

    if data.get("email"):
        update_data["email"] = data["email"]

    if not update_data:
        return jsonify({
            "error": "No data provided for update"
        }), 400

    result = users_collection.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return jsonify({
            "error": "User not found"
        }), 404

    updated_user = users_collection.find_one({
        "user_id": user_id
    })

    return jsonify({
        "id": updated_user["user_id"],
        "name": updated_user["name"],
        "email": updated_user["email"]
    }), 200


# =========================================================
# VOICE PROCESSING
# =========================================================

@app.route("/voice", methods=["POST"])
def process_voice():

    if "audio" not in request.files:
        return jsonify({
            "error": "Audio file is required"
        }), 400

    audio = request.files["audio"]

    temp_path = None

    try:

        # =====================================================
        # SAVE AUDIO TEMPORARILY
        # =====================================================

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp_file:

            audio.save(temp_file.name)
            temp_path = temp_file.name

        # =====================================================
        # VOICE -> TEXT
        # =====================================================

        text = transcribe_audio(temp_path)

        print("\nTranscribed Text:")
        print(text)

        # =====================================================
        # TEXT -> USER DATA
        # =====================================================

        user = parse_user(text)

        print("\nParsed User:")
        print(user)

        action = user.get("action")

        # =====================================================
        # CREATE
        # =====================================================

        if action == "create":

            name = user.get("name")
            email = user.get("email")
            email_confident = user.get(
                "email_confident",
                False
            )

            # Do not save user if name is missing
            if not name:

                return jsonify({
                    "error": (
                        "Could not understand the name. "
                        "Please repeat your name."
                    ),
                    "transcript": text
                }), 400

            # Do not save user if email is missing
            # or LLM is not confident about the email
            if not email or not email_confident:

                return jsonify({
                    "error": (
                        "Email is not valid. "
                        "Please repeat your email."
                    ),
                    "transcript": text
                }), 400

            user_id = get_next_user_id()

            new_user = {
                "user_id": user_id,
                "name": name,
                "email": email
            }

            users_collection.insert_one(new_user)

            created_user = {
                "id": user_id,
                "name": name,
                "email": email
            }

            return jsonify({
                "transcript": text,
                "action": "CREATE",
                "user": created_user
            }), 201

        # =====================================================
        # UPDATE
        # =====================================================

        elif action == "update":

            user_id = user.get("id")

            if not user_id:

                return jsonify({
                    "transcript": text,
                    "action": "UPDATE",
                    "error": (
                        "Please specify the user ID to update"
                    )
                }), 400

            update_data = {}

            if user.get("name"):
                update_data["name"] = user["name"]

            if user.get("email"):
                update_data["email"] = user["email"]

            if not update_data:

                return jsonify({
                    "transcript": text,
                    "action": "UPDATE",
                    "error": "No update data found"
                }), 400

            result = users_collection.update_one(
                {"user_id": int(user_id)},
                {"$set": update_data}
            )

            if result.matched_count == 0:

                return jsonify({
                    "transcript": text,
                    "action": "UPDATE",
                    "error": "User not found"
                }), 404

            updated_user = users_collection.find_one({
                "user_id": int(user_id)
            })

            return jsonify({
                "transcript": text,
                "action": "UPDATE",
                "user": {
                    "id": updated_user["user_id"],
                    "name": updated_user["name"],
                    "email": updated_user["email"]
                }
            }), 200

        # =====================================================
        # SHOW USERS
        # =====================================================

        elif action == "show":

            # Optional user ID
            user_id = user.get("id")

            # Optional user name
            name = user.get("name")

            # -------------------------------------------------
            # SHOW BY USER ID
            # -------------------------------------------------

            if user_id is not None:

                found_users = list(
                    users_collection.find({
                        "user_id": int(user_id)
                    })
                )

            # -------------------------------------------------
            # SHOW BY NAME
            # -------------------------------------------------

            elif name:

                found_users = list(
                    users_collection.find({
                        "name": {
                            "$regex": f"^{name.strip()}$",
                            "$options": "i"
                        }
                    })
                )

            # -------------------------------------------------
            # SHOW ALL USERS
            # -------------------------------------------------

            else:

                found_users = list(
                    users_collection.find()
                )

            # -------------------------------------------------
            # FORMAT USERS
            # -------------------------------------------------

            users = []

            for db_user in found_users:

                # IMPORTANT:
                # Ignore old/incomplete MongoDB documents
                # that don't have user_id.
                if "user_id" not in db_user:
                    continue

                users.append({
                    "id": db_user.get("user_id"),
                    "name": db_user.get("name"),
                    "email": db_user.get("email")
                })

            # -------------------------------------------------
            # NO VALID USERS FOUND
            # -------------------------------------------------

            if not users:

                return jsonify({
                    "transcript": text,
                    "action": "SHOW",
                    "users": [],
                    "count": 0,
                    "message": "No valid users found"
                }), 404

            # -------------------------------------------------
            # RETURN USERS
            # -------------------------------------------------

            return jsonify({
                "transcript": text,
                "action": "SHOW",
                "users": users,
                "count": len(users)
            }), 200

        # =====================================================
        # UNKNOWN ACTION
        # =====================================================

        return jsonify({
            "transcript": text,
            "error": (
                "Could not determine "
                "CREATE, UPDATE or SHOW action"
            )
        }), 400

    except Exception as e:

        print("Error:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=7000,
        debug=True
    )