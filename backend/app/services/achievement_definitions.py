# ==================================================================
# FORGE - ACHIEVEMENT DEFINITIONS
# ==================================================================

from dataclasses import dataclass

# Achievement (Data)
@dataclass(frozen=True)
class AchievementDef:
    code: str
    title: str
    description: str
    flavor: str 

# Achiement definitions
ACHIEVEMENTS: list[AchievementDef] = [
    AchievementDef(
        code="internship",
        title="Internship",
        description="Complete 100 missions",
        flavor="Look at you, doing actual work. Don't get used to being paid, though.",
    ),
    AchievementDef(
        code="full_time",
        title="Full-Time",
        description="Complete 1,000 missions",
        flavor="You still haven't asked for a vacation? Management loves you.",
    ),
    AchievementDef(
        code="senior",
        title="Senior",
        description="Complete 10,000 missions",
        flavor="HR stopped sending you birthday emails. They assume you'll outlive the company.",
    ),
    AchievementDef(
        code="weekly_report",
        title="Weekly Report",
        description="Maintain a 7 day streak",
        flavor="Seven days, zero absences. Technically that makes you Employee of the Week. Your photo goes on the wall. Nobody looks at the wall.",
    ),
    AchievementDef(
        code="pizza_party",
        title="Pizza Party",
        description="Maintain a 30 day streak",
        flavor="Perfect attendance! Your reward is a lukewarm slice of pepperoni. Don't eat it all in your 15-minute break.",
    ),
    AchievementDef(
        code="all_in",
        title="All In",
        description="Max out any single attribute",
        flavor="Full commitment to one area of your life. The other six opened a ticket. Status: unassigned.",
    ),
    AchievementDef(
        code="overqualified",
        title="Overqualified",
        description="Accumulate 1,000,000 XP",
        flavor="Maximum efficiency! No budget for promotions, your base salary remains the same.",
    ),
    AchievementDef(
        code="inventory",
        title="Inventory",
        description="Accumulate 1,000,000 materials",
        flavor="Resource management! You are hoarding enough supplies to survive the apocalypse.",
    ),
    AchievementDef(
        code="supernova",
        title="Supernova",
        description="Accumulate 1,000,000 Stardust",
        flavor="Stellar output! The Council has reviewed your numbers. They will not grant you the rank of Master.",
    ),
    AchievementDef(
        code="initial_commit",
        title="Initial Commit",
        description="Unlock your first perk",
        flavor="You spent imaginary points on imaginary buffs. Welcome to professional development.",
    ),
    AchievementDef(
        code="merged",
        title="Merged",
        description="Max out any perk",
        flavor="Approved, merged, deployed. The error logs are someone else's weekend.",
    ),
    AchievementDef(
        code="first_steps",
        title="First Steps",
        description="Reach Prestige 1",
        flavor="Database wiped! All that hard work melted back into raw data. Absolute genius.",
    ),
    AchievementDef(
        code="worn_path",
        title="Worn Path",
        description="Reach Prestige 25",
        flavor="Infinite loop! You are still staring at the same layout. Don't worry, the pixels aren't going anywhere.",
    ),
    AchievementDef(
        code="no_turning_back",
        title="No Turning Back",
        description="Reach Prestige 50",
        flavor="System broken! Congratulations on your dedication to losing absolutely everything. Truly, a master of self-sabotage.",
    ),
    AchievementDef(
        code="special",
        title="S.P.E.C.I.A.L.",
        description="Max out all attributes",
        flavor="Vault-Tec approved! Maximum potential achieved. Unfortunately, this doesn't transfer to your actual resume. Congratulations you are special!",
    ),
]

# Map of achievement codes 
ACHIEVEMENT_MAP: dict[str, AchievementDef] = {a.code: a for a in ACHIEVEMENTS}
