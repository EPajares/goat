"use client";

import { useTheme } from "@mui/material";
import { ToastContainer, Zoom } from "react-toastify";

interface ToastProviderProps {
  children: React.ReactNode;
}

export default function ToastProvider({ children }: ToastProviderProps) {
  const theme = useTheme();
  return (
    <>
      {children}
      {/* react-toastify v9 ships its defaults via `ToastContainer.defaultProps`, which React 19
       * ignores on function components. Without them `autoClose` is undefined, the progress bar
       * renders as "controlled" at 0 and never fires the animationend that dismisses the toast.
       * Pass them explicitly until the library is upgraded to a React 19 compatible version. */}
      <ToastContainer
        transition={Zoom}
        position="top-center"
        hideProgressBar
        theme={theme.palette.mode}
        autoClose={5000}
        closeOnClick
        pauseOnHover
        pauseOnFocusLoss
        draggable
        draggablePercent={80}
        draggableDirection="x"
        role="alert"
      />
    </>
  );
}
