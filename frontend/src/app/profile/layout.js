import ProfileNavBar from '@/components/utils/ProfileNavBar';
import { IoReturnUpBackOutline } from "react-icons/io5";
import Link from 'next/link';
import Button from '@/components/utils/Button';

export default function ProfileLayout({ children }) {
  return (
    <div className="min-h-screen bg-white">
      <header className="w-full flex items-center justify-center text-[#822433] pt-2 fixed top-0 bg-white z-50 shadow-sm">
              <img src="/logo.png" alt="logo_img" className="w-10 h-10 object-contain mb-1" />
              <Link href="/" className="text-3xl font-bold tracking-wider">
                FAQBuddy
              </Link>
      </header>
      <ProfileNavBar />
      <div className="px-6 pt-15">
        <Link href="/homepage/chat">
          <Button>
            <IoReturnUpBackOutline className="text-xl" />
          </Button>
        </Link>
      </div>
      <main className="pt-4">{children}</main>
    </div>
  );
}