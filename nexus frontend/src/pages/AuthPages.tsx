import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Eye, EyeOff, ShieldCheck, ArrowRight, Lock, Mail, User } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, setCurrentPage } = useApp();
  const [email, setEmail] = useState('you@example.com');
  const [password, setPassword] = useState('••••••••');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login(email);
  };

  return (
    <div className="min-h-screen bg-[#18110c] text-[#fbf8f2] flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-16 h-16 rounded-2xl bg-[#f25c24] mx-auto p-2.5 shadow-xl shadow-[#f25c24]/20 flex items-center justify-center">
            <img src="/nexus_logo.png" alt="NEXUS" className="w-full h-full object-contain filter invert" />
          </div>
          <h1 className="font-serif-brand text-4xl font-bold tracking-wider text-white">
            NEXUS
          </h1>
          <h2 className="text-sm font-semibold text-[#f25c24] max-w-xs mx-auto leading-tight">
            Networked Executive for eXtensible Understanding & Self-learning
          </h2>
          <p className="text-xs text-[#a08c7e] italic">where agents connect to think</p>
        </div>

        {/* Login Card */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-3xl p-8 shadow-2xl space-y-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-[#c7bbb0] block mb-1">
                Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#8e7869] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full bg-[#18110c] border border-[#3b271d] focus:border-[#f25c24] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-[#8e7869] focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#c7bbb0] block mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#8e7869] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-[#18110c] border border-[#3b271d] focus:border-[#f25c24] rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-[#8e7869] focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#8e7869] hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-[#f25c24] hover:bg-[#d94c17] text-white font-bold py-3 rounded-xl shadow-lg shadow-[#f25c24]/20 flex items-center justify-center gap-2 text-xs transition-all hover:scale-[1.01]"
            >
              <span>Sign in</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="text-center pt-2 text-xs text-[#8e7869]">
            Don't have an account?{' '}
            <button
              onClick={() => setCurrentPage('register')}
              className="text-[#f25c24] font-semibold hover:underline"
            >
              Create an account
            </button>
          </div>
        </div>

        {/* Privacy Footer Badge */}
        <div className="flex items-center justify-center gap-2 text-xs text-[#8e7869]">
          <ShieldCheck className="w-4 h-4 text-[#f25c24]" />
          <span>100% local · private by default</span>
        </div>
      </div>
    </div>
  );
};

export const RegisterPage: React.FC = () => {
  const { register, setCurrentPage } = useApp();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim() && email.trim()) {
      register(name, email);
    }
  };

  return (
    <div className="min-h-screen bg-[#18110c] text-[#fbf8f2] flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-[#f25c24] mx-auto p-2 shadow-xl shadow-[#f25c24]/20 flex items-center justify-center">
            <img src="/nexus_logo.png" alt="NEXUS" className="w-full h-full object-contain filter invert" />
          </div>
          <h1 className="font-serif-brand text-3xl font-bold tracking-wider text-white">
            Create your local NEXUS account
          </h1>
          <p className="text-xs text-[#a08c7e]">
            Account data stays securely on your machine in local PostgreSQL.
          </p>
        </div>

        <div className="bg-[#241710] border border-[#3d291d] rounded-3xl p-8 shadow-2xl space-y-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-[#c7bbb0] block mb-1">
                Full name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-[#8e7869] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Arjun Sharma"
                  className="w-full bg-[#18110c] border border-[#3b271d] focus:border-[#f25c24] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-[#8e7869] focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#c7bbb0] block mb-1">
                Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#8e7869] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full bg-[#18110c] border border-[#3b271d] focus:border-[#f25c24] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-[#8e7869] focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#c7bbb0] block mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#8e7869] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[#18110c] border border-[#3b271d] focus:border-[#f25c24] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-[#8e7869] focus:outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-[#f25c24] hover:bg-[#d94c17] text-white font-bold py-3 rounded-xl shadow-lg shadow-[#f25c24]/20 flex items-center justify-center gap-2 text-xs transition-all hover:scale-[1.01]"
            >
              <span>Create account</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="text-center pt-2 text-xs text-[#8e7869]">
            Already have an account?{' '}
            <button
              onClick={() => setCurrentPage('login')}
              className="text-[#f25c24] font-semibold hover:underline"
            >
              Sign in
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
