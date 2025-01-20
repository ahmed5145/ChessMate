import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { toast } from "react-hot-toast";
import UserProfile from "../UserProfile";
import { getUserProfile, updateUserProfile } from "../../api";

// Mock the modules
jest.mock("react-hot-toast");
jest.mock("../../api");

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

const mockProfile = {
  username: "testuser",
  email: "test@example.com",
  rating: 1500,
  preferences: {
    emailNotifications: true,
    darkMode: false,
    autoAnalyze: true,
  },
};

describe("UserProfile Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    getUserProfile.mockResolvedValue(mockProfile);
  });

  it("renders the user profile with loading state initially", () => {
    render(
      <BrowserRouter>
        <UserProfile />
      </BrowserRouter>
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders the user profile information after loading", async () => {
    render(
      <BrowserRouter>
        <UserProfile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue("testuser")).toBeInTheDocument();
      expect(screen.getByDisplayValue("test@example.com")).toBeInTheDocument();
      expect(screen.getByDisplayValue("1500")).toBeInTheDocument();
    });

    expect(screen.getByText("Email Notifications")).toBeInTheDocument();
    expect(screen.getByText("Dark Mode")).toBeInTheDocument();
    expect(screen.getByText("Auto-Analyze Games")).toBeInTheDocument();
  });

  it("handles preference toggles", async () => {
    render(
      <BrowserRouter>
        <UserProfile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Email Notifications")).toBeInTheDocument();
    });

    const emailNotificationsToggle = screen.getByRole("button", {
      name: /email notifications/i,
    });
    const darkModeToggle = screen.getByRole("button", { name: /dark mode/i });
    const autoAnalyzeToggle = screen.getByRole("button", {
      name: /auto-analyze games/i,
    });

    fireEvent.click(emailNotificationsToggle);
    fireEvent.click(darkModeToggle);

    expect(emailNotificationsToggle).toHaveClass("bg-gray-200");
    expect(darkModeToggle).toHaveClass("bg-indigo-600");
    expect(autoAnalyzeToggle).toHaveClass("bg-indigo-600");
  });

  it("handles successful profile update", async () => {
    const updatedProfile = {
      ...mockProfile,
      preferences: {
        emailNotifications: false,
        darkMode: true,
        autoAnalyze: true,
      },
    };
    updateUserProfile.mockResolvedValueOnce(updatedProfile);

    render(
      <BrowserRouter>
        <UserProfile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Email Notifications")).toBeInTheDocument();
    });

    const emailNotificationsToggle = screen.getByRole("button", {
      name: /email notifications/i,
    });
    const darkModeToggle = screen.getByRole("button", { name: /dark mode/i });
    const saveButton = screen.getByRole("button", { name: "Save Changes" });

    fireEvent.click(emailNotificationsToggle);
    fireEvent.click(darkModeToggle);
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(updateUserProfile).toHaveBeenCalledWith({
        preferences: {
          emailNotifications: false,
          darkMode: true,
          autoAnalyze: true,
        },
      });
      expect(toast.success).toHaveBeenCalledWith("Profile updated successfully");
    });
  });

  it("handles profile update error", async () => {
    const mockError = { error: "Failed to update profile" };
    updateUserProfile.mockRejectedValueOnce(mockError);

    render(
      <BrowserRouter>
        <UserProfile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Email Notifications")).toBeInTheDocument();
    });

    const emailNotificationsToggle = screen.getByRole("button", {
      name: /email notifications/i,
    });
    const saveButton = screen.getByRole("button", { name: "Save Changes" });

    fireEvent.click(emailNotificationsToggle);
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(updateUserProfile).toHaveBeenCalled();
      expect(toast.error).toHaveBeenCalledWith(mockError.error);
    });
  });

  it("redirects to login on unauthorized error", async () => {
    getUserProfile.mockRejectedValueOnce({ status: 401 });

    render(
      <BrowserRouter>
        <UserProfile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });

  it("shows loading state during profile update", async () => {
    updateUserProfile.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <BrowserRouter>
        <UserProfile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Email Notifications")).toBeInTheDocument();
    });

    const emailNotificationsToggle = screen.getByRole("button", {
      name: /email notifications/i,
    });
    const saveButton = screen.getByRole("button", { name: "Save Changes" });

    fireEvent.click(emailNotificationsToggle);
    fireEvent.click(saveButton);

    expect(screen.getByText("Saving...")).toBeInTheDocument();
    expect(saveButton).toBeDisabled();
  });
}); 