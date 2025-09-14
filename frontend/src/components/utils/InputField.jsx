import React from 'react';

export default function InputField({ type = "text", name, value, onChange, placeholder, ...props }) {
  return (
    <input
      type={type}
      name={name}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className="w-full border border-gray-300 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#822433] placeholder:italic"
      {...props}
    />
  );
}