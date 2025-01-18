import React, { useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserContext } from '../contexts/UserContext';
import { toast } from 'react-hot-toast';
import { CreditCard } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

const Credits = () => {
  const navigate = useNavigate();
  const { credits, setCredits } = useContext(UserContext);
  const [loading, setLoading] = useState(false);

  const fetchCredits = useCallback(async () => {
    try {
      const accessToken = localStorage.getItem('tokens') ? JSON.parse(localStorage.getItem('tokens')).access : null;
      if (!accessToken) {
        console.error('No access token found');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/credits/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch credits');
      }

      const data = await response.json();
      setCredits(data.credits);
    } catch (error) {
      console.error('Error fetching credits:', error);
      toast.error('Failed to fetch credits');
    }
  }, [setCredits]);

  useEffect(() => {
    fetchCredits();
    // Set up periodic refresh
    const interval = setInterval(fetchCredits, 5000);
    return () => clearInterval(interval);
  }, [fetchCredits]);

  const handlePurchase = async (packageId) => {
    setLoading(true);
    try {
      const accessToken = localStorage.getItem('tokens') ? JSON.parse(localStorage.getItem('tokens')).access : null;
      if (!accessToken) {
        toast.error('Please log in to purchase credits');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/purchase-credits/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          package_id: packageId
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to create checkout session');
      }

      if (!data.checkout_url) {
        throw new Error('No checkout URL received');
      }

      window.location.href = data.checkout_url;
    } catch (error) {
      console.error('Error processing request:', error);
      toast.error(error.message || 'Failed to process request');
    } finally {
      setLoading(false);
    }
  };

  const creditPackages = [
    {
      id: 'basic',
      name: 'Basic Package',
      credits: 100,
      price: 9.99,
      description: 'Perfect for casual players',
      features: [
        '100 game analyses',
        'Basic feedback',
        'Opening suggestions',
        'Valid for 3 months'
      ]
    },
    {
      id: 'pro',
      name: 'Pro Package',
      credits: 300,
      price: 24.99,
      description: 'Great for regular analysis',
      popular: true,
      features: [
        '300 game analyses',
        'Detailed feedback',
        'Opening & middlegame suggestions',
        'Valid for 6 months'
      ]
    },
    {
      id: 'premium',
      name: 'Premium Package',
      credits: 1000,
      price: 79.99,
      description: 'Best value for serious players',
      features: [
        '1000 game analyses',
        'Advanced feedback',
        'Complete game analysis',
        'Valid for 12 months'
      ]
    }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="sm:flex sm:flex-col sm:align-center">
        <h2 className="text-3xl font-extrabold text-gray-900 sm:text-center">Purchase Analysis Credits</h2>
        <p className="mt-5 text-xl text-gray-500 sm:text-center">
          Get credits to analyze your chess games and receive detailed feedback
        </p>
        <div className="mt-4 text-center">
          <span className="inline-flex items-center px-4 py-2 rounded-md bg-indigo-50 text-indigo-700">
            <CreditCard className="h-5 w-5 mr-2" />
            You currently have {credits} credits available
          </span>
        </div>
      </div>

      <div className="mt-12 space-y-4 sm:mt-16 sm:space-y-0 sm:grid sm:grid-cols-2 sm:gap-6 lg:max-w-4xl lg:mx-auto xl:max-w-none xl:mx-0 xl:grid-cols-3">
        {creditPackages.map((pkg) => (
          <div
            key={pkg.id}
            className={`rounded-lg shadow-sm divide-y divide-gray-200 ${
              pkg.popular
                ? 'border-2 border-indigo-500 relative'
                : 'border border-gray-200'
            }`}
          >
            {pkg.popular && (
              <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/2">
                <span className="inline-flex rounded-full bg-indigo-100 px-4 py-1 text-xs font-semibold text-indigo-600">
                  Most Popular
                </span>
              </div>
            )}
            <div className="p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">{pkg.name}</h3>
              <p className="mt-4 text-sm text-gray-500">{pkg.description}</p>
              <p className="mt-8">
                <span className="text-4xl font-extrabold text-gray-900">${pkg.price}</span>
              </p>
              <p className="mt-2 text-sm text-gray-500">for {pkg.credits} credits</p>
              <button
                onClick={() => handlePurchase(pkg.id)}
                disabled={loading}
                className={`mt-8 block w-full bg-${
                  pkg.popular ? 'indigo' : 'gray'
                }-600 hover:bg-${
                  pkg.popular ? 'indigo' : 'gray'
                }-700 text-white font-medium py-2 px-4 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-${
                  pkg.popular ? 'indigo' : 'gray'
                }-500 transition-colors ${
                  loading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {loading ? 'Processing...' : 'Purchase Credits'}
              </button>
            </div>
            <div className="px-6 pt-6 pb-8">
              <h4 className="text-sm font-medium text-gray-900">What's included</h4>
              <ul className="mt-6 space-y-4">
                {pkg.features.map((feature, index) => (
                  <li key={index} className="flex space-x-3">
                    <svg
                      className="flex-shrink-0 h-5 w-5 text-green-500"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-sm text-gray-500">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Credits; 