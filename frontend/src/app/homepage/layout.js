import NavBar from "@/components/utils/NavBar";
import Header from "@/components/utils/Header";
import BackButton from "@/components/utils/BackButton";

export default function HomepageLayout({ children }) {
  return (
    <div className="min-h-screen bg-white">
       <Header/>
      {children}
      <NavBar/>
    </div>
  );
}
