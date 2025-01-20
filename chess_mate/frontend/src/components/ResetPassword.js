import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "react-hot-toast";
import { resetPassword } from "../api";

const validatePassword = (password) => {
  const errors = [];
  if (password.length < 8) {
    errors.push("Password must be at least 8 characters long");
  }
  if (!/[A-Z]/.test(password)) {
    errors.push("Password must contain at least one uppercase letter");
  }
  if (!/[a-z]/.test(password)) {
    errors.push("Password must contain at least one lowercase letter");
  }
  if (!/[0-9]/.test(password)) {
    errors.push("Password must contain at least one number");
  }
  if (!/[!@#$%^&*]/.test(password)) {
    errors.push("Password must contain at least one special character (!@#$%^&*)");
  }
  return errors;
};

const ResetPassword = () => {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);
  const { uid, token } = useParams();
  const navigate = useNavigate();

  const handlePasswordChange = (e) => {
    const password = e.target.value;
    setNewPassword(password);
    setValidationErrors(validatePassword(password));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Check password match
    if (newPassword !== confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }

    // Validate password complexity
    const errors = validatePassword(newPassword);
    if (errors.length > 0) {
      errors.forEach(error => toast.error(error));
      return;
    }

    setLoading(true);
    try {
      await resetPassword(uid, token, newPassword);
      toast.success("Password reset successful!");
      navigate("/password-reset-success");
    } catch (error) {
      console.error("Password reset error:", error);
      const errorMessage = error.message || "An error occurred";
      const errorType = error.error || "";
      
      // Handle specific error cases
      switch (errorType) {
        case "same_password":
          toast.error("New password cannot be the same as your old password");
          break;
        case "complexity":
          toast.error(errorMessage);
          break;
        case "invalid_token":
        case "expired_token":
          navigate("/password-reset-failed");
          break;
        default:
          toast.error(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Reset Your Password
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Please choose a strong password that meets all requirements:
        </p>
        <ul className="mt-2 text-sm text-gray-600 list-disc list-inside">
          <li className={newPassword.length >= 8 ? "text-green-600" : ""}>
            At least 8 characters long
          </li>
          <li className={/[A-Z]/.test(newPassword) ? "text-green-600" : ""}>
            Contains at least one uppercase letter
          </li>
          <li className={/[a-z]/.test(newPassword) ? "text-green-600" : ""}>
            Contains at least one lowercase letter
          </li>
          <li className={/[0-9]/.test(newPassword) ? "text-green-600" : ""}>
            Contains at least one number
          </li>
          <li className={/[!@#$%^&*]/.test(newPassword) ? "text-green-600" : ""}>
            Contains at least one special character (!@#$%^&*)
          </li>
        </ul>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                New Password
              </label>
              <div className="mt-1">
                <input
                  id="newPassword"
                  name="newPassword"
                  type="password"
                  required
                  value={newPassword}
                  onChange={handlePasswordChange}
                  className={`appearance-none block w-full px-3 py-2 border ${
                    validationErrors.length > 0 ? 'border-red-300' : 'border-gray-300'
                  } rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm`}
                />
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirm Password
              </label>
              <div className="mt-1">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={`appearance-none block w-full px-3 py-2 border ${
                    confirmPassword && newPassword !== confirmPassword ? 'border-red-300' : 'border-gray-300'
                  } rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm`}
                />
              </div>
              {confirmPassword && newPassword !== confirmPassword && (
                <p className="mt-2 text-sm text-red-600">
                  Passwords don't match
                </p>
              )}
            </div>

            <div>
              <button
                type="submit"
                disabled={loading || validationErrors.length > 0 || !newPassword || !confirmPassword || newPassword !== confirmPassword}
                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                  loading || validationErrors.length > 0 || !newPassword || !confirmPassword || newPassword !== confirmPassword
                    ? 'bg-indigo-400 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-700'
                } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword; 