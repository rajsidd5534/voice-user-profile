import { useRef, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL;

function App() {
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [action, setAction] = useState("");
  const [user, setUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    try {
      setError("");
      setTranscript("");
      setAction("");
      setUser(null);
      setUsers([]);

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });

        await sendAudioToBackend(audioBlob);
      };

      mediaRecorder.start();

      setRecording(true);
    } catch (err) {
      console.error(err);

      setError(
        "Microphone permission is required. Please allow microphone access."
      );
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
      setRecording(false);
      setProcessing(true);
    }
  };

  const sendAudioToBackend = async (audioBlob) => {
    try {
      const formData = new FormData();

      formData.append("audio", audioBlob, "voice.webm");

      const response = await fetch(`${API_URL}/voice`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong");
      }

      setTranscript(data.transcript);
      setAction(data.action);

      // CREATE / UPDATE
      setUser(data.user || null);

      // SHOW
      setUsers(data.users || []);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="app">
      <div className="card">

        {/* Header */}
        <div className="header">
          <h1>AI User Assistant</h1>
          <p>Voice-based User Management</p>
        </div>

        {/* Microphone */}
        <div className={`mic ${recording ? "recording" : ""}`}>
          🎙️
        </div>

        {/* Status */}
        <div className="status">
          {recording
            ? "Listening..."
            : processing
            ? "Processing your voice..."
            : "Ready to listen"}
        </div>

        {/* Record Button */}
        <button
          className="record-button"
          onClick={recording ? stopRecording : startRecording}
          disabled={processing}
        >
          {recording
            ? "Stop Recording"
            : processing
            ? "Processing..."
            : "Start Voice"}
        </button>

        {/* Voice Instructions */}
        <div className="voice-hint">
          <h3>Try saying</h3>

          <p>
            <strong>Create:</strong>
            <br />
            "Create a new user. My name is Vishal and my email is
            vishal@gmail.com."
          </p>

          <p>
            <strong>Update:</strong>
            <br />
            "Update user 1. Change my name to Raj Kumar and my email to
            rajkumar@gmail.com."
          </p>

          <p>
            <strong>Show by ID:</strong>
            <br />
            "Show user 29."
          </p>

          <p>
            <strong>Show by Name:</strong>
            <br />
            "Show Neha."
            <br />
            "Show users named Neha."
          </p>

          <p>
            <strong>Show by Email:</strong>
            <br />
            "Show neha@gmail.com."
            <br />
            "Show user with email neha@gmail.com."
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {/* Result */}
        {transcript && (
          <>
            {/* Transcript */}
            <div className="section">
              <h3>Transcribed Text</h3>

              <div className="transcript">
                {transcript}
              </div>
            </div>

            {/* Action */}
            <div className="section">
              <h3>Detected Action</h3>

              <div className="action">
                {action}
              </div>
            </div>

            {/* CREATE / UPDATE User */}
            {user && (
              <div className="section">
                <h3>User Profile</h3>

                <div className="profile">
                  <div>
                    <span>👤</span>
                    <strong>{user.name}</strong>
                  </div>

                  <div>
                    <span>✉️</span>
                    <span>{user.email}</span>
                  </div>

                  <div>
                    <span>🆔</span>
                    <span>User ID: {user.id}</span>
                  </div>
                </div>
              </div>
            )}

            {/* SHOW Users */}
            {action === "SHOW" && users.length > 0 && (
              <div className="section">
                <h3>
                  Users Found ({users.length})
                </h3>

                <div className="users-list">
                  {users.map((item) => (
                    <div
                      className="profile"
                      key={item.id}
                    >
                      <div>
                        <span>👤</span>
                        <strong>{item.name}</strong>
                      </div>

                      <div>
                        <span>✉️</span>
                        <span>{item.email}</span>
                      </div>

                      <div>
                        <span>🆔</span>
                        <span>User ID: {item.id}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* SHOW but no users */}
            {action === "SHOW" && users.length === 0 && !error && (
              <div className="error">
                No users found.
              </div>
            )}

            {/* Success Message */}
            <div className="success">
              ✓{" "}
              {action === "CREATE"
                ? "User Created Successfully"
                : action === "UPDATE"
                ? "User Updated Successfully"
                : action === "SHOW"
                ? `${users.length} User${
                    users.length !== 1 ? "s" : ""
                  } Found`
                : "Request Completed Successfully"}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;