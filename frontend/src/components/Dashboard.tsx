'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import useOutreachStore from '@/store/outreach';
import apiService from '@/services/api';
import Button from './Button';
import Input from './Input';
import { useToast } from './ToastProvider';

const SEARCH_STEPS = [
  'Validating your profile',
  'Asking Gemini for structured company matches',
  'Checking company websites (five at a time)',
  'Saving verified results',
];

export const Dashboard: React.FC = () => {
  const { setUserProfile, setCompanyCategories, setIsLoading, isLoading } = useOutreachStore();
  const router = useRouter();
  const notify = useToast();
  const [error, setError] = useState('');
  const [progressStep, setProgressStep] = useState(-1);
  
  const [formData, setFormData] = useState({
    role: '',
    experience: 0,
    skills: '',
    location: '',
    salary: 0,
    num_companies: 10,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'experience' || name === 'salary' || name === 'num_companies' 
        ? parseInt(value) 
        : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.role || !formData.location || !formData.skills) {
      setError('Please fill in the role, skills and location fields.');
      return;
    }

    setError('');
    setIsLoading(true);
    setProgressStep(0);
    const progressTimer = window.setInterval(
      () => setProgressStep(current => Math.min(current + 1, SEARCH_STEPS.length - 2)),
      1800
    );
    
    try {
      const userProfile = {
        role: formData.role,
        experience: formData.experience,
        skills: formData.skills.split(',').map(s => s.trim()),
        location: formData.location,
        salary: formData.salary || undefined,
        num_companies: formData.num_companies,
      };

      setUserProfile(userProfile);

      const response = await apiService.generateCompanies(userProfile);
      setCompanyCategories(response.actively_hiring, response.strategic_targets);
      setProgressStep(SEARCH_STEPS.length - 1);
      notify(`Saved ${response.total} company matches`, 'success');
      router.push('/results');
    } catch (error) {
      console.error('Error generating companies:', error);
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : 'Company search failed. Please try again.';
      setError(message);
      notify('Company search failed', 'error');
    } finally {
      window.clearInterval(progressTimer);
      setIsLoading(false);
      setProgressStep(-1);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">OutreachAI</h1>
        <p className="text-slate-600 mb-8">
          Discover companies and generate personalized cold emails powered by AI
        </p>

        {error && (
          <div role="alert" className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        {isLoading && (
          <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="mb-3 text-sm font-semibold text-blue-900">Search progress</p>
            <ol className="space-y-2 text-sm">
              {SEARCH_STEPS.map((step, index) => (
                <li
                  key={step}
                  className={index <= progressStep ? 'font-medium text-blue-800' : 'text-slate-400'}
                >
                  {index < progressStep ? '✓' : index === progressStep ? '●' : '○'} {step}
                </li>
              ))}
            </ol>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Target Role *
            </label>
            <Input
              type="text"
              name="role"
              placeholder="e.g., Senior Software Engineer"
              value={formData.role}
              onChange={handleChange}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Years of Experience *
              </label>
              <Input
                type="number"
                name="experience"
                min="0"
                max="60"
                value={formData.experience}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Expected Salary (Annual) $
              </label>
              <Input
                type="number"
                name="salary"
                placeholder="Optional"
                value={formData.salary}
                onChange={handleChange}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Key Skills (comma-separated) *
            </label>
            <Input
              type="text"
              name="skills"
              placeholder="e.g., Python, React, Machine Learning"
              value={formData.skills}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Location/Timezone *
            </label>
            <Input
              type="text"
              name="location"
              placeholder="e.g., San Francisco, US or Remote"
              value={formData.location}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Number of Companies to Find
            </label>
            <select
              name="num_companies"
              value={formData.num_companies}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={20}>20</option>
            </select>
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full"
          >
            {isLoading ? 'Finding Companies...' : 'Discover Companies'}
          </Button>
        </form>

        <div className="mt-8 pt-8 border-t border-slate-200">
          <h3 className="font-semibold text-slate-900 mb-4">How It Works</h3>
          <ul className="space-y-2 text-sm text-slate-600">
            <li>✓ Fill in your profile information</li>
            <li>✓ AI finds relevant companies with hiring signals</li>
            <li>✓ Generate personalized cold emails</li>
            <li>✓ Send directly via Gmail</li>
            <li>✓ Track your outreach activities</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
