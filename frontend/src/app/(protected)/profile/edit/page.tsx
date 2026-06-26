'use client';

import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { PreferenceForm } from '@/components/profile/PreferenceForm';
import { getMyProfile, updateMyProfile } from '@/lib/api/profiles';
import type { Profile } from '@/lib/types';

export default function EditProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    getMyProfile().then(setProfile).catch((e) => setMessage(e.message));
  }, []);

  async function handleSave(payload: Partial<Profile>) {
    try {
      await updateMyProfile(payload);
      setMessage('Profile updated successfully.');
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Update failed');
    }
  }

  if (!profile) return <div className="card">Loading profile...</div>;

  return (
    <div>
      <PageHeader title="Edit Profile" subtitle="Real PATCH /profiles/me" />
      <PreferenceForm profile={profile} onSave={handleSave} />
      <div className="space" />
      <div className="muted small">{message}</div>
    </div>
  );
}
