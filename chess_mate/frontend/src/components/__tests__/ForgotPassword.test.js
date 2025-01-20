import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { toast } from "react-hot-toast";
import ForgotPassword from "../ForgotPassword";
import { requestPasswordReset } from "../../api";

// Mock the modules
jest.mock("react-hot-toast");
jest.mock("../../api");

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

describe("ForgotPassword Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the forgot password form", () => {
    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    expect(screen.getByText("Reset your password")).toBeInTheDocument();
    expect(screen.getByLabelText("Email address")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send reset link" })).toBeInTheDocument();
  });

  it("handles successful password reset request", async () => {
    const mockResponse = { message: "Password reset email sent" };
    requestPasswordReset.mockResolvedValueOnce(mockResponse);

    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText("Email address");
    const submitButton = screen.getByRole("button", { name: "Send reset link" });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(requestPasswordReset).toHaveBeenCalledWith({
        email: "test@example.com",
      });
      expect(toast.success).toHaveBeenCalledWith(mockResponse.message);
    });

    // Wait for navigation
    await waitFor(
      () => {
        expect(mockNavigate).toHaveBeenCalledWith("/");
      },
      { timeout: 6000 }
    );
  });

  it("handles password reset request error", async () => {
    const mockError = { error: "Invalid email" };
    requestPasswordReset.mockRejectedValueOnce(mockError);

    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText("Email address");
    const submitButton = screen.getByRole("button", { name: "Send reset link" });

    fireEvent.change(emailInput, { target: { value: "invalid@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(requestPasswordReset).toHaveBeenCalledWith({
        email: "invalid@example.com",
      });
      expect(toast.error).toHaveBeenCalledWith(mockError.error);
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("shows loading state during submission", async () => {
    requestPasswordReset.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText("Email address");
    const submitButton = screen.getByRole("button", { name: "Send reset link" });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.click(submitButton);

    expect(screen.getByText("Sending reset link...")).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });
}); 