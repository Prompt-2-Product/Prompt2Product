import React from 'react';
import { Link } from 'react-router-dom';

const Services = () => {
  return (
    <div className="bg-gray-100 py-8">
      <h2 className="text-4xl text-center font-bold pb-6">Services</h2>
      <div className="grid grid-cols-3 gap-4 mx-auto w-full max-w-7xl">
        <Link to="/service1" className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 cursor-pointer">
          <img src="/images/service1.png" alt="Service 1" className="w-full h-[200px] object-cover mb-4" />
          <h3 className="text-xl font-semibold text-gray-900">Service 1</h3>
          <p className="text-sm text-gray-700">Description for Service 1.</p>
        </Link>
        {/* Add more services as needed */}
      </div>
    </div>
  );
};

export default Services;
