import { Card } from "@/components/ui/Card";

interface SellerQuestionsListProps {
  questions: string[];
}

export function SellerQuestionsList({ questions }: SellerQuestionsListProps) {
  if (questions.length === 0) return null;

  return (
    <Card className="p-6">
      <h2 className="text-lg font-medium">Questions to Ask the Seller</h2>
      <ol className="mt-4 space-y-3">
        {questions.map((question, i) => (
          <li key={i} className="flex gap-3 text-sm">
            <span className="text-muted">{i + 1}.</span>
            <span>{question}</span>
          </li>
        ))}
      </ol>
    </Card>
  );
}
