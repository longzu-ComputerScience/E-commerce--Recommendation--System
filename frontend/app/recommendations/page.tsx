import RecommendationList from "@/components/RecommendationList";

export default function RecommendationsPage() {
  return (
    <div className="animate-fade-in-up">
      <div className="flex items-center gap-3 mb-2">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{
            background:
              "linear-gradient(135deg, rgba(20, 184, 166, 0.2), rgba(56, 189, 248, 0.2))",
            border: "1px solid rgba(20, 184, 166, 0.3)",
          }}
        >
          <span className="text-lg">🎯</span>
        </div>
        <div>
          <h1 className="text-2xl font-bold gradient-text">
            Recommendations
          </h1>
          <p className="text-gray-400 text-sm">
            Personalized product suggestions powered by co-purchase & up-sale
            analysis
          </p>
        </div>
      </div>
      <div className="mt-6">
        <RecommendationList />
      </div>
    </div>
  );
}
