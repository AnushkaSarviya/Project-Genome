import type { NodeType, RelationshipType } from '../types/genome';

export interface StyleConfig {
  color: string;
  bg: string;
  border: string;
  badgeBg: string;
  badgeText: string;
  shape: 'circle' | 'square' | 'triangle' | 'diamond';
  label: string;
}

export const NODE_STYLES: Record<NodeType, StyleConfig> = {
  Repository: {
    color: '#283593', // Deep Indigo
    bg: '#EEF2FF',
    border: '#1A237E',
    badgeBg: '#E8EDFB',
    badgeText: '#1E297A',
    shape: 'circle',
    label: 'Repository',
  },
  Directory: {
    color: '#00695C', // Teal
    bg: '#E0F2F1',
    border: '#004D40',
    badgeBg: '#E6F4F3',
    badgeText: '#004D40',
    shape: 'circle',
    label: 'Directory',
  },
  File: {
    color: '#0277BD', // Slate Blue
    bg: '#E1F5FE',
    border: '#01579B',
    badgeBg: '#E7F5FC',
    badgeText: '#025B8E',
    shape: 'square',
    label: 'File',
  },
  Class: {
    color: '#B25E02', // Warm Ochre
    bg: '#FFF8E1',
    border: '#8E4800',
    badgeBg: '#FDF3D8',
    badgeText: '#874602',
    shape: 'triangle',
    label: 'Class',
  },
  Function: {
    color: '#2E6F40', // Forest Green
    bg: '#E8F5E9',
    border: '#1B5E20',
    badgeBg: '#E8F3E9',
    badgeText: '#1F542E',
    shape: 'circle',
    label: 'Function',
  },
  Method: {
    color: '#558B2F', // Olive Sage
    bg: '#F1F8E9',
    border: '#33691E',
    badgeBg: '#EEF6E6',
    badgeText: '#3D6B20',
    shape: 'circle',
    label: 'Method',
  },
  UnresolvedReference: {
    color: '#C62828', // Crimson Red
    bg: '#FFEBEE',
    border: '#B71C1C',
    badgeBg: '#FCEBEB',
    badgeText: '#9E1C1C',
    shape: 'diamond',
    label: 'Unresolved Reference',
  },
};

export const REL_STYLES: Record<RelationshipType, { color: string; label: string; dash?: string; width: number }> = {
  CONTAINS: {
    color: '#78909C', // Muted Blue Gray
    label: 'CONTAINS (Hierarchy)',
    width: 1.5,
  },
  IMPORTS: {
    color: '#1E88E5', // Crisp Blue
    label: 'IMPORTS (Module Dependency)',
    dash: '4 4',
    width: 2,
  },
  CALLS: {
    color: '#D32F2F', // Crimson Red
    label: 'CALLS (Invocation)',
    width: 2.2,
  },
  INHERITS: {
    color: '#8E24AA', // Purple
    label: 'INHERITS (Subclassing)',
    dash: '6 3 2 3',
    width: 2,
  },
  DEPENDS_ON: {
    color: '#E65100', // Rust Orange
    label: 'DEPENDS_ON (Derived)',
    dash: '2 2',
    width: 2.2,
  },
};
