import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { User, Mail, Settings } from "lucide-react";
import { getUserProfile, updateUserProfile } from "../api";

const UserProfile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    darkMode: false,
    autoAnalyze: true,
  });
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await getUserProfile();
        setProfile(data);
        setPreferences((prev) => ({
          ...prev,
          ...data.preferences,
        }));
      } catch (error) {
        console.error("Error fetching profile:", error);
        toast.error("Failed to load profile");
        if (error.status === 401) {
          navigate("/");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [navigate]);

  const handlePreferenceChange = (key) => {
    setPreferences((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updatedProfile = await updateUserProfile({
        preferences,
      });
      setProfile(updatedProfile);
      toast.success("Profile updated successfully");
    } catch (error) {
      console.error("Error updating profile:", error);
      toast.error(error.error || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center">
              <User className="h-5 w-5 mr-2" />
              Profile Information
            </h3>
            <div className="mt-5 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">Username</label>
                <div className="mt-1 flex items-center">
                  <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                    <User className="h-4 w-4" />
                  </span>
                  <input
                    type="text"
                    value={profile?.username || ""}
                    disabled
                    className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border-gray-300 bg-gray-50 text-gray-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <div className="mt-1 flex items-center">
                  <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                    <Mail className="h-4 w-4" />
                  </span>
                  <input
                    type="email"
                    value={profile?.email || ""}
                    disabled
                    className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border-gray-300 bg-gray-50 text-gray-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Rating</label>
                <div className="mt-1">
                  <input
                    type="number"
                    value={profile?.rating || 1200}
                    disabled
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <h4 className="text-lg font-medium text-gray-900 flex items-center mt-8 mb-4">
                  <Settings className="h-5 w-5 mr-2" />
                  Preferences
                </h4>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="flex-grow flex flex-col">
                      <span className="text-sm font-medium text-gray-900">Email Notifications</span>
                      <span className="text-sm text-gray-500">Receive email notifications for game analysis and updates</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => handlePreferenceChange("emailNotifications")}
                      className={`${
                        preferences.emailNotifications ? "bg-indigo-600" : "bg-gray-200"
                      } relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                    >
                      <span
                        className={`${
                          preferences.emailNotifications ? "translate-x-5" : "translate-x-0"
                        } pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200`}
                      />
                    </button>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex-grow flex flex-col">
                      <span className="text-sm font-medium text-gray-900">Dark Mode</span>
                      <span className="text-sm text-gray-500">Use dark theme for better visibility in low light</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => handlePreferenceChange("darkMode")}
                      className={`${
                        preferences.darkMode ? "bg-indigo-600" : "bg-gray-200"
                      } relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                    >
                      <span
                        className={`${
                          preferences.darkMode ? "translate-x-5" : "translate-x-0"
                        } pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200`}
                      />
                    </button>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex-grow flex flex-col">
                      <span className="text-sm font-medium text-gray-900">Auto-Analyze Games</span>
                      <span className="text-sm text-gray-500">Automatically analyze games after completion</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => handlePreferenceChange("autoAnalyze")}
                      className={`${
                        preferences.autoAnalyze ? "bg-indigo-600" : "bg-gray-200"
                      } relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                    >
                      <span
                        className={`${
                          preferences.autoAnalyze ? "translate-x-5" : "translate-x-0"
                        } pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200`}
                      />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-end">
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className={`inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                  saving ? "opacity-50 cursor-not-allowed" : ""
                }`}
              >
                {saving ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile; 