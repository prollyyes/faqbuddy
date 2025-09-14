'use client'
import { useSwipeable } from 'react-swipeable';
import { useRouter, usePathname } from 'next/navigation';
import { useLogout } from '@/components/utils/LogoutContext';

const pages = [
  '/profile/personalInfo',
  '/profile/courses'
];

export default function SwipeWrapperInsegnante({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const currentIndex = pages.indexOf(pathname);
  const { openLogout } = useLogout();

  const handlers = useSwipeable({
    onSwipedLeft: () => {
      if (currentIndex < pages.length - 1) {
        router.push(pages[currentIndex + 1]);
      } else if (currentIndex !== -1) {
        openLogout();
      }
    },
    onSwipedRight: () => {
      if (currentIndex > 0) router.push(pages[currentIndex - 1]);
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
