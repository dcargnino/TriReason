import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import PromptsPage from "./components/PromptsPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/prompts",
    element: <PromptsPage />,
  },
]);

export default function Root() {
  return <RouterProvider router={router} />;
}
