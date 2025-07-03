import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Header from "@/components/utils/Header";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "FAQBuddy",
  description: "Il tuo assistente smart per domande universitarie.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
        <Header/>
      </body>
    </html>
  );
}
