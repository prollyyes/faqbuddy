'use client'
import { useSwipeable } from 'react-swipeable';
import { useRouter, usePathname } from 'next/navigation';
import { useLogout } from '@/components/utils/LogoutContext';

const pages = [
  '/profile/personalInfo',
  '/profile/courses',
  '/profile/stats'
];

function normalizePath(path) {
  // Rimuove slash finale e query string
  return path.replace(/\/$/, '').split('?')[0];
}

export default function SwipeWrapperStudente({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const normalizedPath = normalizePath(pathname);
  const { openLogout } = useLogout();

  const currentIndex = pages.indexOf(normalizedPath);

  // console.log('normalizedPath:', normalizedPath, 'currentIndex:', currentIndex, 'pathname:', pathname, 'normalizedPath:', normalizedPath);

  const handlers = useSwipeable({
    onSwipedLeft: () => {
      if (currentIndex !== -1) {
        if (currentIndex < pages.length - 1) {
          router.push(pages[currentIndex + 1]);
        } else {
          openLogout();
        }
      }
    },
    onSwipedRight: () => {
      if (currentIndex > 0 && currentIndex !== -1) {
        router.push(pages[currentIndex - 1]);
      }
    },
    trackTouch: true,
    trackMouse: true,
    delta: 1,
  });

  return (
    <div {...handlers} className="h-full w-full">
      {children}
    </div>
  );
}
