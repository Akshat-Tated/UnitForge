import { useState } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { saveApiKey } from "../api/client";

export function SettingsPage() {
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const handleSave = async () => {
    if (!apiKey.trim()) {
      toast.error("Please enter an API key");
      return;
    }
    if (!apiKey.startsWith("AIza")) {
      toast.error("Invalid Gemini API key — should start with AIza");
      return;
    }
    setSaving(true);
    try {
      await saveApiKey(apiKey.trim());
      toast.success("API key saved securely");
      setApiKey("");
    } catch {
      toast.error("Failed to save API key");
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
            onChange={(e) => setApiKey(e.target.value)}
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
                       disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
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
