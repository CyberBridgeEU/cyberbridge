import useCountStore from "../store/useCountStore.ts";

export default function NotFoundPage() {

    const {count} = useCountStore()

    return (<div>{count}</div>)
}
