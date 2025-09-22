import { ArtifactData } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export async function fetchArtifacts(): Promise<ArtifactData[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/artifacts`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch artifacts: ${response.status}`);
    }
    
    const data = await response.json();
    return data.artifacts;
  } catch (error) {
    console.error('Error fetching artifacts:', error);
    return [];
  }
}

export async function createArtifact(title: string, content: string, description?: string): Promise<ArtifactData> {
  const response = await fetch(`${API_BASE_URL}/artifacts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title,
      content,
      description,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create artifact: ${response.status}`);
  }

  return response.json();
}