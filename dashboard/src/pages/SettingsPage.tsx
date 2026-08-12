import { useState } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { saveApiKey } from "../api/client";

export function SettingsPage() {
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [savedStatus, setSavedStatus] = useState(false);
  const navigate = useNavigate();

  const handleSave = async () => {
    setSuccessMsg("");
    setErrorMsg("");
    setSavedStatus(false);

    const trimmedKey = apiKey.trim();

    if (!trimmedKey) {
      setErrorMsg("Gemini API key is required.");
      toast.error("Gemini API key is required.");
      return;
    }
    
    setSaving(true);
    try {
      await saveApiKey(trimmedKey);
      setSuccessMsg("Gemini API key saved successfully.");
      toast.success("Gemini API key saved successfully.");
      setSavedStatus(true);
      setApiKey("");

      setTimeout(() => {
        setSavedStatus(false);
      }, 2000);
    } catch (err: any) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        setErrorMsg("Your session has expired. Please log in again.");
      } else if (err.response?.status >= 400 && err.response?.status < 500) {
        setErrorMsg("Unable to save Gemini API key. Please check the key and try again.");
        toast.error("Unable to save Gemini API key. Please check the key and try again.");
      } else {
        setErrorMsg("Unable to save Gemini API key. Please try again.");
        toast.error("Unable to save Gemini API key. Please try again.");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <button
        onClick={() => navigate("/")}
        className="flex items-center gap-2 text-gray-400
                   hover:text-white mb-8 transition-colors"
      >
        ← Back to Dashboard
      </button>

      <h1 className="text-2xl font-bold mb-2">Settings</h1>
      <p className="text-gray-400 mb-8">
        Manage your profile and AI provider settings
      </p>

      {/* Gemini API Key */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl
                      p-6 max-w-2xl mb-6">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-xl">🔑</span>
          <h2 className="text-lg font-semibold">Gemini API Key</h2>
        </div>
        <p className="text-gray-400 text-sm mb-4">
          UnitForge uses your key for AI test generation — your quota,
          your data relationship with Google. Stored encrypted, never shown again.
          Get one free at{" "}
          <a
            href="https://aistudio.google.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-400 hover:underline"
          >
            aistudio.google.com
          </a>
        </p>
        <div className="flex gap-3">
          <input
            type="password"
            value={apiKey}
            onChange={(e) => {
              setApiKey(e.target.value);
              setSuccessMsg("");
              setErrorMsg("");
              setSavedStatus(false);
            }}
            placeholder="Paste your Gemini API key..."
            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-600
                       rounded-lg text-white placeholder-gray-500
                       focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700
                       rounded-lg text-white font-medium transition-colors
                       disabled:opacity-50 min-w-[120px]"
          >
            {saving ? "Saving..." : savedStatus ? "Saved ✓" : "Save"}
          </button>
        </div>

        {successMsg && (
          <p className="text-sm text-emerald-400 mt-2 flex items-center gap-1">
            ✓ {successMsg}
          </p>
        )}
        {errorMsg && (
          <p className="text-sm text-rose-400 mt-2 flex items-center gap-1">
            ✕ {errorMsg}
          </p>
        )}

        <p className="text-xs text-gray-500 mt-3">
          Your key is encrypted before storage. UnitForge only uses it
          for your test generation requests.
        </p>
      </div>

      {/* Info */}
      <p className="text-xs text-gray-500 max-w-2xl">
        UnitForge is open source · MIT license ·
        your data stays in your account and your AI key stays yours
      </p>
    </div>
  );
}
