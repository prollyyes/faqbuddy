import React, { forwardRef } from 'react';
import { Slot } from '@radix-ui/react-slot';
import clsx from 'clsx';

// -----------------------------------------------------------------------------
// <Button /> — minimal, framework-agnostic React component (ESNext, .jsx)
// -----------------------------------------------------------------------------
// • Variants:   default | outline | ghost | link
// • Sizes:     sm | md | lg
// • `asChild`: render another element (e.g. <Link>) while inheriting styles.
// -----------------------------------------------------------------------------
// NOTE: This file is plain JavaScript/JSX — no TypeScript types.
// -----------------------------------------------------------------------------

const variantClasses = {
  default: 'bg-white text-[#822433] hover:bg-[#822433] hover:text-white border border-[#822433]',
  outline: 'border border-[#822433] text-[#822433] hover:bg-[#822433]/5',
  ghost: 'text-[#822433] hover:bg-[#822433]/10',
  link: 'text-[#822433] underline-offset-4 hover:underline'
};

const sizeClasses = {
  sm: 'h-8 px-3 text-sm rounded-lg',
  md: 'h-10 px-4 text-sm rounded-xl',
  lg: 'h-12 px-6 text-base rounded-2xl'
};

const Button = forwardRef(
  (
    {
      variant = 'default',
      size = 'md',
      asChild = false,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? Slot : 'button';

    return (
      <Comp
        ref={ref}
        className={clsx(
          'inline-flex items-center justify-center font-bold transition-colors disabled:opacity-50 disabled:pointer-events-none',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {children}
      </Comp>
    );
  }
);

Button.displayName = 'Button';

export { Button };
export default Button;