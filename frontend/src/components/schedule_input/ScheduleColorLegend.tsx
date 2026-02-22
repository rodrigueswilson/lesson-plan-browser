export function ScheduleColorLegend() {
  return (
    <div className="space-y-3">
      <div className="text-sm text-muted-foreground">
        <p>
          <strong>Note:</strong> For non-class periods (PREP, Lunch, A.M. Routine, Dismissal, PLC,
          GLM), grade and homeroom will be automatically cleared.
        </p>
      </div>

      <div className="border rounded-lg p-4 bg-card">
        <h3 className="text-sm font-semibold mb-3">Color Legend</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-gray-300 bg-gray-100"></div>
            <span>PREP</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-blue-200 bg-blue-50"></div>
            <span>A.M. Routine</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-orange-200 bg-orange-50"></div>
            <span>Lunch</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-purple-200 bg-purple-50"></div>
            <span>Dismissal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-amber-300 bg-amber-50"></div>
            <span>PLC / GLM (meetings)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-green-300 bg-green-50"></div>
            <span>ELA</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-blue-300 bg-blue-50"></div>
            <span>MATH</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-yellow-300 bg-yellow-50"></div>
            <span>Science</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-red-300 bg-red-50"></div>
            <span>Social Studies</span>
          </div>
        </div>
      </div>
    </div>
  );
}
