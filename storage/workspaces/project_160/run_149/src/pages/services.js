import React from 'react';
import Link from 'next/link';

function ServicesPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <h1 className="text-4xl font-bold mb-8 text-gray-700">Services</h1>
      <div className="grid grid-cols-3 gap-8">
        <Link href="/services/web-development" passHref>
          <a className="bg-white shadow-md p-6 rounded-lg hover:bg-gray-200 transition duration-300">
            <h2 className="text-xl font-bold text-gray-700 mb-4">Web Development</h2>
            <p className="text-gray-500">Create a robust and scalable web application.</p>
          </a>
        </Link>
        <Link href="/services/mobile-development" passHref>
          <a className="bg-white shadow-md p-6 rounded-lg hover:bg-gray-200 transition duration-300">
            <h2 className="text-xl font-bold text-gray-700 mb-4">Mobile Development</h2>
            <p className="text-gray-500">Build apps for iOS and Android.</p>
          </a>
        </Link>
        <Link href="/services/seo" passHref>
          <a className="bg-white shadow-md p-6 rounded-lg hover:bg-gray-200 transition duration-300">
            <h2 className="text-xl font-bold text-gray-700 mb-4">SEO</h2>
            <p className="text-gray-500">Optimize your website for search engines.</p>
          </a>
        </Link>
      </div>
    </div>
  );
}

export default ServicesPage;
