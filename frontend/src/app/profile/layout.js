import ProfileNavBar from '@/components/utils/ProfileNavBar';
import Header from '@/components/utils/Header';
import BackButton from '@/components/utils/BackButton';

export default function ProfileLayout({ children }) {
  return (
    <div className="min-h-screen bg-white ">
      <Header />
      <ProfileNavBar />
      <main className="pt-4">{children}</main>
    </div>
  );
}