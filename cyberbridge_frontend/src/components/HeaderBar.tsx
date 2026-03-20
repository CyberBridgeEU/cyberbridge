// src/components/HeaderBar.tsx
import useUserStore from "../store/useUserStore.ts";

export default function HeaderBar() {
    const { current_user } = useUserStore()

    return (
        <div className={'headerbar-parent'}>
            <img
                src={current_user?.organisation_logo || "/cyberbridge_logo.svg"}
                alt={current_user?.organisation_logo ? `${current_user.organisation_name} Logo` : "CyberBridge Logo"}
                className="headerbar-logo-main"
                style={{ marginTop: '7px', marginLeft: '7px' }}
                onError={(e) => {
                    // Fallback to default logo if organization logo fails to load
                    e.currentTarget.src = "/cyberbridge_logo.svg";
                    e.currentTarget.alt = "CyberBridge Logo";
                }}
            />
        </div>
    )
}
