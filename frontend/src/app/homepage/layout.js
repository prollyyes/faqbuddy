import NavBar from "@/components/utils/NavBar";
import Link from "next/link";

export default function HomepageLayout({ children }) {
  return (
    <div className="min-h-screen bg-white">
        <header className="w-full flex items-center justify-center text-[#822433] pt-2 fixed top-0 bg-white z-50 shadow-sm">
              <img src="/logo.png" alt="logo_img" className="w-10 h-10 object-contain mb-1" />
              <Link href="/" className="text-3xl font-bold tracking-wider">
                FAQBuddy
              </Link>
      </header>
      {children}
      <NavBar />
    </div>
  );
}
