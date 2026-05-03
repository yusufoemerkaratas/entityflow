import { createBrowserRouter } from "react-router-dom"

import { AppLayout } from "./layouts/AppLayout"
import { DocumentDetailPage } from "./pages/DocumentDetailPage"
import { HomePage } from "./pages/HomePage"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: "documents/:id",
        element: <DocumentDetailPage />,
      },
    ],
  },
])