# pip3 install click --target boss

PROJECT_ROOT="$HOME/projects/boss/boss"
BOSS_DIR='boss'

cd $PROJECT_ROOT

for d in $(find -iname '*__pycache__' -type d); do
    rm -rf "$d"
done

if python3 -m zipapp --compress --python "/usr/bin/env python3" $BOSS_DIR; then
    echo "Boss built, $(du -h $PROJECT_ROOT/boss.pyz | cut -f1)"
fi


