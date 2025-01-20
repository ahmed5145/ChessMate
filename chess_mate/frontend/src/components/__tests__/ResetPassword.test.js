import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { toast } from "react-hot-toast";
import ResetPassword from "../ResetPassword";
import { resetPassword } from "../../api";

// Mock the modules
jest.mock("react-hot-toast");
jest.mock("../../api");

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
  useParams: () => ({ token: "test-token" }),
}));

describe("ResetPassword Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the reset password form", () => {
    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    expect(screen.getByText("Set new password")).toBeInTheDocument();
    expect(screen.getByLabelText("New Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm New Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset password" })).toBeInTheDocument();
  });

  it("handles successful password reset", async () => {
    const mockResponse = { message: "Password reset successful" };
    resetPassword.mockResolvedValueOnce(mockResponse);

    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const passwordInput = screen.getByLabelText("New Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm New Password");
    const submitButton = screen.getByRole("button", { name: "Reset password" });

    fireEvent.change(passwordInput, { target: { value: "newpassword123" } });
    fireEvent.change(confirmPasswordInput, { target: { value: "newpassword123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(resetPassword).toHaveBeenCalledWith({
        token: "test-token",
        password: "newpassword123",
      });
      expect(toast.success).toHaveBeenCalledWith(mockResponse.message);
    });

    // Wait for navigation
    await waitFor(
      () => {
        expect(mockNavigate).toHaveBeenCalledWith("/");
      },
      { timeout: 4000 }
    );
  });

  it("handles password reset error", async () => {
    const mockError = { error: "Invalid token" };
    resetPassword.mockRejectedValueOnce(mockError);

    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const passwordInput = screen.getByLabelText("New Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm New Password");
    const submitButton = screen.getByRole("button", { name: "Reset password" });

    fireEvent.change(passwordInput, { target: { value: "newpassword123" } });
    fireEvent.change(confirmPasswordInput, { target: { value: "newpassword123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(resetPassword).toHaveBeenCalledWith({
        token: "test-token",
        password: "newpassword123",
      });
      expect(toast.error).toHaveBeenCalledWith(mockError.error);
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("shows error when passwords do not match", async () => {
    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const passwordInput = screen.getByLabelText("New Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm New Password");
    const submitButton = screen.getByRole("button", { name: "Reset password" });

    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.change(confirmPasswordInput, { target: { value: "password456" } });
    fireEvent.click(submitButton);

    expect(toast.error).toHaveBeenCalledWith("Passwords do not match");
    expect(resetPassword).not.toHaveBeenCalled();
  });

  it("shows loading state during submission", async () => {
    resetPassword.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const passwordInput = screen.getByLabelText("New Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm New Password");
    const submitButton = screen.getByRole("button", { name: "Reset password" });

    fireEvent.change(passwordInput, { target: { value: "newpassword123" } });
    fireEvent.change(confirmPasswordInput, { target: { value: "newpassword123" } });
    fireEvent.click(submitButton);

    expect(screen.getByText("Resetting password...")).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });
}); 