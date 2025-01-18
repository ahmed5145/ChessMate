import React, { useState, useEffect } from 'react';
import { CreditCard, Package, Zap, Shield } from 'lucide-react';
import { toast } from 'react-toastify';

const CREDIT_PACKAGES = [
  {
    id: 'basic',
    name: 'Basic',
    credits: 10,
    price: 4.99,
    icon: Package,
    description: 'Perfect for casual players',
  },
  {
    id: 'pro',
    name: 'Pro',
    credits: 50,
    price: 19.99,
    icon: Zap,
    description: 'Most popular for regular players',
    featured: true,
  },
  {
    id: 'unlimited',
    name: 'Elite',
    credits: 200,
    price: 49.99,
    icon: Shield,
    description: 'Best value for serious players',
  },
];

const Credits = () => {
  const [credits, setCredits] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCredits();
  }, []);

  const fetchCredits = async () => {
    try {
      const response = await fetch('/api/credits');
      const data = await response.json();
      setCredits(data.credits);
    } catch (error) {
      console.error('Error fetching credits:', error);
    }
  };

  const handlePurchase = async (packageId) => {
    setLoading(true);
    try {
      // TODO: Implement Stripe integration
      const response = await fetch('/api/purchase-credits', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ packageId }),
      });

      if (!response.ok) {
        throw new Error('Purchase failed');
      }

      const data = await response.json();
      setCredits(data.newCredits);
      toast.success('Credits purchased successfully!');
    } catch (error) {
      console.error('Error purchasing credits:', error);
      toast.error('Failed to purchase credits. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center">
        <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
          Purchase Analysis Credits
        </h2>
        <p className="mt-4 text-xl text-gray-600">
          Get credits to analyze your chess games and receive detailed feedback
        </p>
      </div>

      <div className="mt-8 flex items-center justify-center">
        <div className="inline-flex items-center px-4 py-2 rounded-md bg-gray-100">
          <CreditCard className="h-5 w-5 text-gray-500 mr-2" />
          <span className="text-gray-900 font-medium">{credits} credits remaining</span>
        </div>
      </div>

      <div className="mt-12 space-y-4 sm:mt-16 sm:space-y-0 sm:grid sm:grid-cols-2 sm:gap-6 lg:max-w-4xl lg:mx-auto xl:max-w-none xl:mx-0 xl:grid-cols-3">
        {CREDIT_PACKAGES.map((pkg) => (
          <div
            key={pkg.id}
            className={`rounded-lg shadow-sm divide-y divide-gray-200 ${
              pkg.featured
                ? 'border-2 border-indigo-500 relative'
                : 'border border-gray-200'
            }`}
          >
            {pkg.featured && (
              <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/2">
                <span className="inline-flex rounded-full bg-indigo-100 px-4 py-1 text-xs font-semibold text-indigo-600">
                  Popular
                </span>
              </div>
            )}
            <div className="p-6">
              <div className="flex items-center">
                <pkg.icon className={`h-8 w-8 ${pkg.featured ? 'text-indigo-500' : 'text-gray-500'}`} />
                <h3 className="ml-4 text-xl font-semibold text-gray-900">{pkg.name}</h3>
              </div>
              <p className="mt-4 text-sm text-gray-500">{pkg.description}</p>
              <p className="mt-8">
                <span className="text-4xl font-extrabold text-gray-900">${pkg.price}</span>
              </p>
              <p className="mt-2 text-sm text-gray-500">for {pkg.credits} credits</p>
              <button
                onClick={() => handlePurchase(pkg.id)}
                disabled={loading}
                className={`mt-8 block w-full bg-${
                  pkg.featured ? 'indigo' : 'gray'
                }-600 hover:bg-${
                  pkg.featured ? 'indigo' : 'gray'
                }-700 text-white font-medium py-2 px-4 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-${
                  pkg.featured ? 'indigo' : 'gray'
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
                <li className="flex space-x-3">
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
                  <span className="text-sm text-gray-500">
                    {pkg.credits} game analyses
                  </span>
                </li>
                <li className="flex space-x-3">
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
                  <span className="text-sm text-gray-500">
                    Detailed game feedback
                  </span>
                </li>
                <li className="flex space-x-3">
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
                  <span className="text-sm text-gray-500">
                    AI-powered analysis
                  </span>
                </li>
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Credits; 