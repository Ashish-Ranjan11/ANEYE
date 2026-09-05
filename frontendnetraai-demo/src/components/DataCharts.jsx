export function DataBarChart({
  title,
  data,
  suffix = "",
  maxValue,
}) {

  const actualMax =
    maxValue ||
    Math.max(
      ...data.map(
        (x) =>
          Number(
            x.value || 0
          )
      ),
      1
    );


  return (

    <div className="data-chart">

      <h4>
        {title}
      </h4>


      <div className="data-bars">

        {data.map(
          (item) => {

            const value =
              Number(
                item.value || 0
              );

            const width =
              Math.min(
                value /
                  actualMax *
                  100,
                100
              );


            return (

              <div
                className="data-bar-row"
                key={item.label}
              >

                <span>
                  {item.label}
                </span>


                <div className="data-bar-track">

                  <div
                    className="data-bar-fill"
                    style={{
                      width:
                        `${width}%`
                    }}
                  />

                </div>


                <strong>
                  {value.toFixed(
                    item.decimals ?? 1
                  )}
                  {suffix}
                </strong>

              </div>

            );

          }
        )}

      </div>

    </div>

  );

}


export function Gauge({
  value,
  label,
  subtitle,
}) {

  const n =
    Math.max(
      0,
      Math.min(
        Number(value || 0),
        100
      )
    );


  return (

    <div className="gauge-card">

      <div
        className="gauge-ring"
        style={{
          "--gauge":
            `${n * 3.6}deg`
        }}
      >

        <div>

          <strong>
            {n.toFixed(1)}
          </strong>

          <span>
            /100
          </span>

        </div>

      </div>


      <h4>
        {label}
      </h4>

      {subtitle && (
        <p>
          {subtitle}
        </p>
      )}

    </div>

  );

}