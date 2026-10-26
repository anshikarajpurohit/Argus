import {useState,useEffect} from 'react';
import {api,message} from '../api';
export function useData(path, refresh = 0) {
  const [data, setData] = useState(null),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api
      .get(path)
      .then((r) => {
        if (active) {
          setData(r.data);
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError(message(e));
      });
    return () => {
      active = false;
    };
  }, [path, refresh]);
  return { data, setData, error };
}
