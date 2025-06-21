import ProfileNavBar from '@/components/utils/ProfileNavBar';
import Header from '@/components/utils/Header';
import Link from 'next/link';
import Button from '@/components/utils/Button';
import { IoReturnUpBackOutline } from "react-icons/io5";
import BackButton from '@/components/utils/BackButton';

export default function ProfileLayout({ children }) {
  return (
    <div className="min-h-screen bg-white">
      <Header />
      <div className="fixed pt-24 pl-4">
        <BackButton href="/homepage/chat" />
      </div>
      <ProfileNavBar />
      <main className="pt-4">{children}</main>
    </div>
  );
}