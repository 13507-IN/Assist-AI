'use client';

import React, { useState } from 'react';
import useOutreachStore from '@/store/outreach';
import apiService from '@/services/api';
import Button from './Button';
import { Company } from '@/types';

interface CompanyCardProps {
  company: Company;
  onSelect: (company: Company) => void;
}

const CompanyCard: React.FC<CompanyCardProps> = ({ company, onSelect }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <h3 className="text-lg font-semibold text-slate-900 mb-2">{company.name}</h3>
      
      {company.website && (
        <p className="text-sm text-blue-600 mb-2">
          <a href={company.website} target="_blank" rel="noopener noreferrer">
            {company.website}
          </a>
        </p>
      )}
      
      <div className="flex gap-2 mb-4">
        <span className={`text-xs px-2 py-1 rounded ${
          company.hiring_signal === 'active'
            ? 'bg-green-100 text-green-800'
            : 'bg-yellow-100 text-yellow-800'
        }`}>
          {company.hiring_signal === 'active' ? 'Actively Hiring' : 'Strategic Target'}
        </span>
        <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">
          Relevance: {(company.relevance_score * 100).toFixed(0)}%
        </span>
      </div>
      
      {company.summary && (
        <p className="text-sm text-slate-600 mb-4 line-clamp-2">{company.summary}</p>
      )}
      
      <Button
        variant="primary"
        size="sm"
        onClick={() => onSelect(company)}
        className="w-full"
      >
        Generate Email
      </Button>
    </div>
  );
};

export const ResultsPage: React.FC = () => {
  const {
    activelyHiring,
    strategicTargets,
    setSelectedCompany,
    isLoading,
  } = useOutreachStore();

  const [showEmailModal, setShowEmailModal] = useState(false);
  const [selectedCompany, setSelected] = useState<Company | null>(null);

  const handleSelectCompany = (company: Company) => {
    setSelected(company);
    setSelectedCompany(company);
    setShowEmailModal(true);
  };

  if (isLoading) {
    return (
      <div className="w-full flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-xl text-slate-600">Analyzing companies...</p>
        </div>
      </div>
    );
  }

  const totalCompanies = activelyHiring.length + strategicTargets.length;

  return (
    <div className="w-full max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">Discovery Results</h1>
        <p className="text-slate-600">Found {totalCompanies} relevant companies</p>
      </div>

      {activelyHiring.length > 0 && (
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-green-700 mb-4 flex items-center gap-2">
            <span className="text-3xl">🔥</span> Actively Hiring ({activelyHiring.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {activelyHiring.map(company => (
              <CompanyCard
                key={company.id}
                company={company}
                onSelect={handleSelectCompany}
              />
            ))}
          </div>
        </div>
      )}

      {strategicTargets.length > 0 && (
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-blue-700 mb-4 flex items-center gap-2">
            <span className="text-3xl">🎯</span> Strategic Targets ({strategicTargets.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {strategicTargets.map(company => (
              <CompanyCard
                key={company.id}
                company={company}
                onSelect={handleSelectCompany}
              />
            ))}
          </div>
        </div>
      )}

      {totalCompanies === 0 && (
        <div className="text-center py-12">
          <p className="text-lg text-slate-600">No companies found. Try adjusting your search criteria.</p>
          <Button
            variant="primary"
            className="mt-4"
            onClick={() => window.location.href = '/'}
          >
            New Search
          </Button>
        </div>
      )}

      {showEmailModal && selectedCompany && (
        <EmailModal
          company={selectedCompany}
          onClose={() => {
            setShowEmailModal(false);
            setSelected(null);
          }}
        />
      )}
    </div>
  );
};

interface EmailModalProps {
  company: Company;
  onClose: () => void;
}

const EmailModal: React.FC<EmailModalProps> = ({ company, onClose }) => {
  const { generatedEmail, setGeneratedEmail, isLoading, setIsLoading, userProfile } = useOutreachStore();
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateEmail = async () => {
    if (!userProfile) return;

    setIsGenerating(true);
    try {
      const email = await apiService.generateEmail(
        'user-id', // TODO: Get from auth context
        company.id,
        company.name,
        company.summary || 'No summary available',
        userProfile.role,
        userProfile.skills
      );
      setGeneratedEmail(email);
    } catch (error) {
      console.error('Error generating email:', error);
      alert('Error generating email');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSendEmail = async () => {
    if (!generatedEmail) return;

    setIsLoading(true);
    try {
      const result = await apiService.sendEmail(
        'user-id', // TODO: Get from auth context
        'recipient@example.com', // TODO: Get from email editor
        company.id,
        company.name,
        generatedEmail.subject,
        generatedEmail.body
      );

      if (result.success) {
        alert('Email sent successfully!');
        onClose();
      } else {
        alert('Error sending email: ' + result.error);
      }
    } catch (error) {
      console.error('Error sending email:', error);
      alert('Error sending email');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-slate-100 px-6 py-4 border-b border-slate-200 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-slate-900">Email for {company.name}</h2>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-700 text-2xl"
          >
            ✕
          </button>
        </div>

        <div className="p-6">
          {!generatedEmail ? (
            <div className="text-center py-8">
              <p className="text-slate-600 mb-6">Generate a personalized email for this company</p>
              <Button
                variant="primary"
                size="lg"
                onClick={handleGenerateEmail}
                disabled={isGenerating}
              >
                {isGenerating ? 'Generating Email...' : 'Generate Email'}
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Subject
                </label>
                <input
                  type="text"
                  value={generatedEmail.subject}
                  readOnly
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Email Body
                </label>
                <textarea
                  value={generatedEmail.body}
                  readOnly
                  rows={10}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50"
                />
              </div>

              <div className="flex gap-4">
                <Button
                  variant="primary"
                  onClick={handleSendEmail}
                  disabled={isLoading}
                  className="flex-1"
                >
                  {isLoading ? 'Sending...' : 'Send Email'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleGenerateEmail}
                  disabled={isGenerating}
                  className="flex-1"
                >
                  Regenerate
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
