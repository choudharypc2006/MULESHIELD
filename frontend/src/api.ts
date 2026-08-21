import { AccountSummary, AccountDetail } from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchAccounts(): Promise<AccountSummary[]> {
  const response = await fetch(`${API_BASE}/accounts`);
  if (!response.ok) throw new Error('Failed to fetch accounts');
  return response.json();
}

export async function fetchAccountDetails(id: number): Promise<AccountDetail> {
  const response = await fetch(`${API_BASE}/accounts/${id}`);
  if (!response.ok) throw new Error('Failed to fetch account details');
  return response.json();
}

export async function submitAction(id: number, action: 'mule' | 'clear' | 'escalate'): Promise<AccountDetail> {
  const response = await fetch(`${API_BASE}/accounts/${id}/action`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ action }),
  });
  if (!response.ok) throw new Error('Failed to submit action');
  return response.json();
}
