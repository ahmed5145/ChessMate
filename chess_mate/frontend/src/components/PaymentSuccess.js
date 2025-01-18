import React, { useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { CheckCircle } from 'lucide-react';
import { UserContext } from '../contexts/UserContext';

const API_BASE_URL = 'http://localhost:8000/api';

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const [sessionProcessed, setSessionProcessed] = useState(false);
  const { setCredits, fetchCredits } = useContext(UserContext);
  const MAX_RETRIES = 3;

  useEffect(() => {
    const confirmPayment = async () => {
      try {
        // Don't retry if we've already successfully processed this session
        if (sessionProcessed) {
          return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('session_id');
        
        if (!sessionId) {
          toast.error('No session ID found');
          setTimeout(() => navigate('/credits'), 3000);
          return;
        }

        const accessToken = localStorage.getItem('tokens') ? JSON.parse(localStorage.getItem('tokens')).access : null;
        if (!accessToken) {
          toast.error('Please log in to confirm your purchase');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        // First confirm the purchase
        console.log('Confirming payment at:', `${API_BASE_URL}/confirm-purchase/`);
        const response = await fetch(`${API_BASE_URL}/confirm-purchase/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
          },
          body: JSON.stringify({ session_id: sessionId })
        });

        // Log raw response for debugging
        const responseText = await response.text();
        console.log('Raw confirm purchase response:', responseText);

        let data;
        try {
          data = JSON.parse(responseText);
        } catch (e) {
          console.error('Failed to parse response:', e);
          throw new Error('Invalid response from server');
        }

        if (response.ok && data.success) {
          setSessionProcessed(true);
          // Update credits in context
          setCredits(data.credits);
          // Trigger a fresh fetch to ensure all components are in sync
          await fetchCredits();
          
          // Show success message with the credits from the confirmation response
          const message = data.already_processed 
            ? `Payment was already processed. Your current balance is ${data.credits} credits.`
            : `Successfully added ${data.added_credits} credits! Your new balance is ${data.credits} credits.`;
          toast.success(message);
          setIsProcessing(false);
          setTimeout(() => navigate('/credits'), 3000);
        } else if (response.status === 500 && retryCount < MAX_RETRIES && !data.already_processed) {
          // Only retry if it's a 500 error, we haven't exceeded retries, and it wasn't already processed
          console.log(`Retry attempt ${retryCount + 1} of ${MAX_RETRIES}`);
          setRetryCount(prev => prev + 1);
          setTimeout(confirmPayment, 1000); // Wait 1 second before retrying
        } else {
          throw new Error(data.error || data.details || 'Failed to confirm purchase');
        }
      } catch (error) {
        console.error('Error confirming payment:', error);
        toast.error(error.message || 'Failed to confirm payment');
        setIsProcessing(false);
        setTimeout(() => navigate('/credits'), 3000);
      }
    };

    confirmPayment();
  }, [navigate, retryCount, sessionProcessed, setCredits, fetchCredits]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center">
            <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
            <h2 className="mt-4 text-2xl font-medium text-gray-900">
              {isProcessing ? 'Processing Payment...' : 'Payment Successful!'}
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              {isProcessing 
                ? retryCount > 0 
                  ? `Retrying confirmation... (Attempt ${retryCount} of ${MAX_RETRIES})`
                  : 'Please wait while we confirm your purchase.'
                : 'Thank you for your purchase. Your credits have been added to your account.'}
            </p>
            {!isProcessing && (
              <p className="mt-4 text-sm text-gray-500">
                Redirecting you back to the credits page...
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentSuccess; 