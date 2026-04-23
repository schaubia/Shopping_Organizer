import { Allergen } from "@/types";
import clsx from "clsx";

const SEVERITY_STYLES: Record<string, string> = {
  high:   "bg-red-100   text-red-700   border-red-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low:    "bg-gray-100  text-gray-600  border-gray-200",
};

export default function AllergenBadge({ allergen, severity }: Allergen) {
  return (
    <span className={clsx(
      "text-xs font-medium px-2 py-0.5 rounded-full border capitalize",
      SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.low
    )}>
      {allergen.replace("_", " ")}
    </span>
  );
}
