export interface College {
  name: string;
  shortName: string;
  domain: string;
}

export const COLLEGE_DOMAINS: { [key: string]: College } = {
  'pomona.edu': {
    name: 'Pomona College',
    shortName: 'Pomona',
    domain: 'pomona.edu'
  },
  'hmc.edu': {
    name: 'Harvey Mudd College',
    shortName: 'Harvey Mudd',
    domain: 'hmc.edu'
  },
  'scrippscollege.edu': {
    name: 'Scripps College',
    shortName: 'Scripps',
    domain: 'scrippscollege.edu'
  },
  'pitzer.edu': {
    name: 'Pitzer College',
    shortName: 'Pitzer',
    domain: 'pitzer.edu'
  },
  'cmc.edu': {
    name: 'Claremont McKenna College',
    shortName: 'CMC',
    domain: 'cmc.edu'
  },
  'andrew.cmu.edu': {
    name: 'Carnegie Mellon University',
    shortName: 'CMU',
    domain: 'andrew.cmu.edu'
  }
};

export const validateCollegeEmail = (email: string): { isValid: boolean; college?: College; error?: string } => {
  if (!email || !email.includes('@')) {
    return { isValid: false, error: 'Invalid email format' };
  }

  const domain = email.split('@')[1]?.toLowerCase();
  
  if (!domain?.endsWith('.edu')) {
    return { isValid: false, error: 'Only .edu email addresses are allowed' };
  }

  // Check if it's a known college from our legacy mapping
  const college = COLLEGE_DOMAINS[domain];
  
  if (college) {
    return { isValid: true, college };
  }

  // For unknown domains, let the backend AI handle validation
  // Return as valid so the request goes to the backend
  return { 
    isValid: true, 
    college: {
      name: 'Unknown University',
      shortName: 'Unknown',
      domain: domain
    }
  };
};

export const getCollegeFromEmail = (email: string): College | null => {
  const domain = email.split('@')[1]?.toLowerCase();
  return COLLEGE_DOMAINS[domain] || null;
};

export const getAllColleges = (): College[] => {
  return Object.values(COLLEGE_DOMAINS);
};