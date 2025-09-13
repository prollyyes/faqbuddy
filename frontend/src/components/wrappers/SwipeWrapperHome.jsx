import { useSwipeable } from 'react-swipeable';
import { useRouter, usePathname } from 'next/navigation';

const pages = [
  '/homepage/materials',
  '/homepage/chat',
  '/profile/personalInfo'
];

export default function SwipeWrapperHome({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const currentIndex = pages.indexOf(pathname);

  const handlers = useSwipeable({
    onSwipedLeft: () => {
      if (currentIndex < pages.length - 1) router.push(pages[currentIndex + 1]);
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