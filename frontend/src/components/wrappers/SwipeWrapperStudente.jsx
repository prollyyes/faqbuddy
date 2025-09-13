import { useSwipeable } from 'react-swipeable';
import { useRouter, usePathname } from 'next/navigation';

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

  const currentIndex = pages.indexOf(normalizedPath);

  // console.log('normalizedPath:', normalizedPath, 'currentIndex:', currentIndex, 'pathname:', pathname, 'normalizedPath:', normalizedPath);

  const handlers = useSwipeable({
    onSwipedLeft: () => {
      if (currentIndex < pages.length - 1 && currentIndex !== -1) {
        router.push(pages[currentIndex + 1]);
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