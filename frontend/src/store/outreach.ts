import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserProfile, Company, Email } from '@/types';

interface OutreachStore {
  // User
  userId: string;
  userProfile: UserProfile | null;
  setUserProfile: (profile: UserProfile) => void;

  // Companies
  companies: Company[];
  setCompanies: (companies: Company[]) => void;
  activelyHiring: Company[];
  strategicTargets: Company[];
  setCompanyCategories: (active: Company[], strategic: Company[]) => void;

  // Current selection
  selectedCompany: Company | null;
  setSelectedCompany: (company: Company | null) => void;

  // Email
  generatedEmail: Email | null;
  setGeneratedEmail: (email: Email | null) => void;

  // Loading states
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Reset
  reset: () => void;
}

const useOutreachStore = create<OutreachStore>()(persist((set) => ({
  userId: 'local-user',
  userProfile: null,
  setUserProfile: (profile) => set({ userProfile: profile }),

  companies: [],
  setCompanies: (companies) => set({ companies }),
  activelyHiring: [],
  strategicTargets: [],
  setCompanyCategories: (active, strategic) =>
    set({ activelyHiring: active, strategicTargets: strategic }),

  selectedCompany: null,
  setSelectedCompany: (company) => set({ selectedCompany: company }),

  generatedEmail: null,
  setGeneratedEmail: (email) => set({ generatedEmail: email }),

  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),

  reset: () =>
    set({
      userProfile: null,
      companies: [],
      activelyHiring: [],
      strategicTargets: [],
      selectedCompany: null,
      generatedEmail: null,
      isLoading: false,
    }),
}), {
  name: 'outreach-ai-state',
  partialize: (state) => ({
    userId: state.userId,
    userProfile: state.userProfile,
    companies: state.companies,
    activelyHiring: state.activelyHiring,
    strategicTargets: state.strategicTargets,
    selectedCompany: state.selectedCompany,
    generatedEmail: state.generatedEmail,
  }),
}));

export default useOutreachStore;
