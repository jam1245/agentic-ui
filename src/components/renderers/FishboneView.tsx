import type { FishbonePayload } from "../../contract";

/** Structured (not pixel-perfect) Ishikawa view: the problem at the head, causes
 *  grouped into category "bones". A real fishbone SVG can replace this later — the
 *  contract (problem + category/cause rows) stays the same. */
export function FishboneView({ payload }: { payload: FishbonePayload }) {
  const categories = [...new Set(payload.data.map((d) => d.category))];
  return (
    <div className="agent-ui-fishbone">
      <div className="agent-ui-fishbone-head">{payload.problem}</div>
      <div className="agent-ui-fishbone-bones">
        {categories.map((cat) => (
          <div key={cat} className="agent-ui-fishbone-bone">
            <div className="agent-ui-fishbone-category">{cat}</div>
            <ul>
              {payload.data
                .filter((d) => d.category === cat)
                .map((d, i) => (
                  <li key={i}>{d.cause}</li>
                ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
