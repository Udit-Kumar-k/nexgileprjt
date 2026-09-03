import { create } from 'zustand';

interface FilterState {
  reportingYear: number;
  entityId: string;
  facilityId: string;
  period: string;
  setReportingYear: (year: number) => void;
  setEntityId: (id: string) => void;
  setFacilityId: (id: string) => void;
  setPeriod: (period: string) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  reportingYear: 2024,
  entityId: '',
  facilityId: '',
  period: '',

  setReportingYear: (reportingYear) => set({ reportingYear }),
  setEntityId: (entityId) => set({ entityId, facilityId: '' }),
  setFacilityId: (facilityId) => set({ facilityId }),
  setPeriod: (period) => set({ period }),
  resetFilters: () => set({ entityId: '', facilityId: '', period: '' }),
}));
