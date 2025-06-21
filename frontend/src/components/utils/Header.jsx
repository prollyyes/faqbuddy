import Link from 'next/link';


export default function Header() {
  return (
    <header className="w-full h-20 flex items-center justify-center text-[#822433] pt-2 fixed top-0 bg-white z-50 shadow-sm">
      <Link href="/" className="text-4xl font-bold tracking-wider mr-2">
        FAQBuddy
      </Link>
      <img src="/logo.png" alt="logo_img" className="w-12 h-12 object-contain mb-1" />
    </header>
  );
}
