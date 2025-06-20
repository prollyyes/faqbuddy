import ProfileNavBar from '@/components/utils/ProfileNavBar';
import { IoReturnUpBackOutline } from "react-icons/io5";
import Link from 'next/link';

export default function ProfileLayout({ children }) {
  return (
    <div className="min-h-screen bg-white">
      <ProfileNavBar />
      <div className="px-6 pt-4">
        <Link
          href="/chat"
          className="inline-block text-[#800020] border-2 border-[#800020] px-4 py-1 rounded-md hover:bg-[#800020] hover:text-white transition font-semibold"
        >
          <IoReturnUpBackOutline className="text-xl" />
        </Link>
      </div>
      <main className="pt-4">{children}</main>
    </div>
  );
}