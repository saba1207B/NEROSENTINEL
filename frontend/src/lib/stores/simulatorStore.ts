import { create } from 'zustand';

interface SimulatorState {
  ensoStrength: number; // 0 to 100
  temperatureAnomaly: number; // -5 to +5
  precipitationMultiplier: number; // 0.5 to 1.5
  simulationMonths: number; // 1 to 24
  isRunning: boolean;
  setEnsoStrength: (val: number) => void;
  setTemperatureAnomaly: (val: number) => void;
  setPrecipitationMultiplier: (val: number) => void;
  setSimulationMonths: (val: number) => void;
  setIsRunning: (val: boolean) => void;
  reset: () => void;
}

export const useSimulatorStore = create<SimulatorState>((set) => ({
  ensoStrength: 50,
  temperatureAnomaly: 1.5,
  precipitationMultiplier: 0.8,
  simulationMonths: 12,
  isRunning: false,
  setEnsoStrength: (val) => set({ ensoStrength: val }),
  setTemperatureAnomaly: (val) => set({ temperatureAnomaly: val }),
  setPrecipitationMultiplier: (val) => set({ precipitationMultiplier: val }),
  setSimulationMonths: (val) => set({ simulationMonths: val }),
  setIsRunning: (val) => set({ isRunning: val }),
  reset: () => set({ 
    ensoStrength: 50, 
    temperatureAnomaly: 1.5, 
    precipitationMultiplier: 0.8, 
    simulationMonths: 12 
  }),
}));
